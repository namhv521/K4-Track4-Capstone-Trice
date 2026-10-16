import csv
import json
import tempfile
import unittest
from pathlib import Path
from evaluate import evaluate, EVENT_FIELDS, LABEL_FIELDS


class EvaluationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[1] / 'evidence')
        self.root = Path(self.tmp.name)
        self.addCleanup(self.tmp.cleanup)

    def score(self, events, labels, frames=None):
        for name, fields, values in [('events.csv', EVENT_FIELDS, events), ('labels.csv', LABEL_FIELDS, labels)]:
            with (self.root / name).open('w', newline='', encoding='utf-8') as out:
                writer = csv.DictWriter(out, fieldnames=fields)
                writer.writeheader()
                writer.writerows(values)
        if frames:
            (self.root / 'frames.jsonl').write_text('\n'.join(json.dumps(f) for f in frames), encoding='utf-8')
        return evaluate(str(self.root / 'events.csv'), str(self.root / 'labels.csv'), str(self.root))

    def label(self, sid='p', positive=True, leave=1):
        return dict(session_id=sid, scenario_id='synthetic', is_abandoned=int(positive), t_leave_s=leave,
                    t_return_s='', t_end_s=20, notes='SYNTHETIC: not live evidence')

    def event(self, sid='p', t=6, kind='UNATTENDED_ALERT', episode='e', ident='id'):
        return dict(session_id=sid, event_id=ident, episode_id=episode, type=kind, t_s=t,
                    seat_id='A', person_id=1, object_id=2, reason='synthetic')

    def test_half_precision_recall_and_reminder_separate(self):
        result = self.score([self.event(), self.event('n'), self.event(t=1, kind='REMINDER', ident='r')],
                            [self.label(), self.label('p2'), self.label('n', False)])
        self.assertEqual((result['tp'], result['fp'], result['fn']), (1, 1, 1))
        self.assertEqual((result['precision'], result['recall']), (.5, .5))
        self.assertEqual(result['reminder']['matched'], 1)
        self.assertIsNone(result['reminder']['association_accuracy'])

    def test_duplicate_cannot_increase_tp(self):
        result = self.score([self.event(), self.event(t=7, ident='again'), self.event(t=8, ident='other', episode='other')], [self.label()])
        self.assertEqual((result['tp'], result['fp'], result['duplicate_events']), (1, 1, 1))

    def test_early_late_alerts_and_boundaries(self):
        for t, expected in [(5.99, (0, 1, 1)), (6, (1, 0, 0)), (9, (1, 0, 0)), (9.01, (0, 1, 1))]:
            with self.subTest(t=t):
                r = self.score([self.event(t=t)], [self.label()])
                self.assertEqual((r['tp'], r['fp'], r['fn']), expected)

    def test_undefined_ratios(self):
        r = self.score([], [self.label('n', False, '')])
        self.assertIsNone(r['precision'])
        self.assertIsNone(r['recall'])
        self.assertEqual(r['tn_sessions'], 1)

    def test_uncertainty_excludes_gaps_and_final_frame(self):
        frames = [dict(session_id='p', observation={'t_s': t}, decision={'state': s}, processing_ms=ms)
                  for t, s, ms in [(0, 'UNCERTAIN', 10), (.25, 'ATTENDED', 20), (.5, 'UNCERTAIN', 30), (2, 'UNCERTAIN', 40)]]
        r = self.score([], [self.label()], frames)['frames']
        self.assertEqual((r['covered_s'], r['uncertain_s'], r['gap_s']), (.5, .25, 1.5))
        self.assertEqual(r['uncertain_fraction'], .5)
        self.assertEqual(r['processing_ms']['p50'], 25)
        self.assertEqual(r['processing_ms']['p95'], 38.5)

    def test_rejects_unlabeled_session_and_invalid_time(self):
        with self.assertRaises(ValueError):
            self.score([self.event('unknown')], [self.label()])
        with self.assertRaises(ValueError):
            self.score([self.event(t=float('nan'))], [self.label()])
        with self.assertRaises(ValueError):
            self.score([], [self.label(), self.label()])


if __name__ == '__main__':
    unittest.main()
