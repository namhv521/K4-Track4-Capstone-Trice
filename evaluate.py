"""Offline event scorer. Ground truth must be annotated independently."""
import argparse
import csv
import json
import math
from pathlib import Path

EVENT_FIELDS = ['session_id', 'event_id', 'episode_id', 'type', 't_s', 'seat_id', 'person_id', 'object_id', 'reason']
LABEL_FIELDS = ['session_id', 'scenario_id', 'is_abandoned', 't_leave_s', 't_return_s', 't_end_s', 'notes']


def rows(path, fields):
    with open(path, encoding='utf-8-sig', newline='') as stream:
        reader = csv.DictReader(stream)
        if not set(fields).issubset(reader.fieldnames or []):
            raise ValueError('Missing required CSV columns: ' + str(path))
        return list(reader)


def number(value):
    value = float(value)
    if not math.isfinite(value) or value < 0:
        raise ValueError('Times must be finite and nonnegative')
    return value


def summary(values):
    values = sorted(values)
    def percentile(p):
        if not values:
            return None
        index = (len(values) - 1) * p
        low = int(index)
        return values[low] + (values[min(low + 1, len(values) - 1)] - values[low]) * (index - low)
    return {'n': len(values), 'p50': percentile(.5), 'p95': percentile(.95)}


def evaluate(events_path: str, labels_path: str, frames_dir: str) -> dict:
    labels = {}
    for row in rows(labels_path, LABEL_FIELDS):
        sid = row['session_id']
        if not sid or sid in labels:
            raise ValueError('Exactly one independently labeled scenario per session required')
        if row['is_abandoned'] not in ('0', '1'):
            raise ValueError('is_abandoned must be 0 or 1')
        for field in ('t_leave_s', 't_return_s', 't_end_s'):
            row[field] = number(row[field]) if row[field] else None
        leave, end, returned = row['t_leave_s'], row['t_end_s'], row['t_return_s']
        if end is None or leave is not None and leave > end or returned is not None and (leave is None or not leave <= returned <= end):
            raise ValueError('Invalid label time ordering or missing end time')
        if row['is_abandoned'] == '1' and (leave is None or leave + 5 > end or returned is not None and returned < leave + 5):
            raise ValueError('Positive session requires an observable five-second unattended interval')
        labels[sid] = row
    seen, ids, details, alerts, reminders = set(), set(), [], [], []
    duplicates = 0
    for event in sorted(rows(events_path, EVENT_FIELDS), key=lambda e: number(e['t_s'])):
        sid, kind = event['session_id'], event['type']
        if sid not in labels or kind not in ('REMINDER', 'UNATTENDED_ALERT'):
            raise ValueError('Unlabeled event session or unknown event type')
        event['t_s'] = number(event['t_s'])
        if event['t_s'] > labels[sid]['t_end_s']:
            raise ValueError('Event outside labeled interval')
        if not event['event_id'] or not event['episode_id']:
            raise ValueError('Event and episode IDs required')
        key, ident = (sid, event['episode_id'], kind), (sid, event['event_id'])
        if key in seen or ident in ids:
            duplicates += 1
            details.append({**event, 'outcome': 'DUPLICATE'})
            continue
        seen.add(key)
        ids.add(ident)
        (alerts if kind == 'UNATTENDED_ALERT' else reminders).append(event)
    matched, reminder_matched, delays, reminder_delays = set(), set(), [], []
    for event in alerts:
        sid, t = event['session_id'], event['t_s']
        label = labels[sid]
        leave = label['t_leave_s']
        valid = label['is_abandoned'] == '1' and sid not in matched and leave + 5 <= t <= min(leave + 8, label['t_end_s'])
        if valid:
            matched.add(sid)
            delays.append(t - leave)
        details.append({**event, 'outcome': 'TP' if valid else 'FP'})
    for event in reminders:
        sid, t = event['session_id'], event['t_s']
        leave = labels[sid]['t_leave_s']
        valid = leave is not None and sid not in reminder_matched and leave <= t <= min(leave + 3, labels[sid]['t_end_s'])
        if valid:
            reminder_matched.add(sid)
            reminder_delays.append(t - leave)
        details.append({**event, 'outcome': 'REMINDER_MATCH' if valid else 'REMINDER_UNMATCHED'})
    tp, fp = len(matched), len(alerts) - len(matched)
    positives = sum(r['is_abandoned'] == '1' for r in labels.values())
    alert_sessions = {e['session_id'] for e in alerts}
    result = {'sessions': len(labels), 'positive_sessions': positives, 'tp': tp, 'fp': fp, 'fn': positives - tp,
              'tn_sessions': sum(r['is_abandoned'] == '0' and sid not in alert_sessions for sid, r in labels.items()),
              'precision': tp / (tp + fp) if tp + fp else None, 'recall': tp / positives if positives else None,
              'duplicate_events': duplicates, 'alert_delay_total_s': summary(delays),
              'reminder': {'matched': len(reminder_matched), 'unmatched': len(reminders) - len(reminder_matched),
                           'delay_s': summary(reminder_delays), 'association_accuracy': None,
                           'association_note': 'Requires independent person/object identity annotations, absent from label schema.'},
              'per_event': details}
    processing, previous = [], {}
    uncertain = covered = gaps = 0.0
    paths = []
    if frames_dir:
        path = Path(frames_dir)
        if not path.exists():
            raise FileNotFoundError(path)
        paths = [path] if path.is_file() else sorted(path.rglob('frames.jsonl'))
    for path in paths:
        for line in path.read_text(encoding='utf-8').splitlines():
            if not line.strip():
                continue
            record = json.loads(line)
            sid = record['session_id']
            if sid not in labels:
                continue
            t = number(record['observation']['t_s'])
            if t > labels[sid]['t_end_s']:
                raise ValueError('Frame outside labeled interval')
            if sid in previous:
                last_t, state = previous[sid]
                dt = t - last_t
                if dt <= 0:
                    raise ValueError('Frame timestamps must strictly increase per session')
                if dt <= .5:
                    covered += dt
                    uncertain += dt if state == 'UNCERTAIN' else 0
                else:
                    gaps += dt
            previous[sid] = t, record['decision']['state']
            processing.append(number(record['processing_ms']))
    result['frames'] = {'n': len(processing), 'processing_ms': summary(processing), 'covered_s': covered,
                        'gap_s': gaps, 'uncertain_s': uncertain, 'uncertain_fraction': uncertain / covered if covered else None,
                        'method': 'Left-state intervals <=0.5s; gaps and final frame excluded.'}
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--events', required=True)
    parser.add_argument('--labels', required=True)
    parser.add_argument('--frames', default='')
    parser.add_argument('--output')
    args = parser.parse_args()
    content = json.dumps(evaluate(args.events, args.labels, args.frames), ensure_ascii=False, indent=2, allow_nan=False)
    if args.output:
        path = Path(args.output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content + '\n', encoding='utf-8')
    print(content)


if __name__ == '__main__':
    main()
