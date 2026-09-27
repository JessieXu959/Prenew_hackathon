import csv
import io
import unittest
from prenew_import import HEADERS
from server import import_csv, APIError

class PrenewImportTests(unittest.TestCase):
    def data(self,rows,delimiter=','):
        text=io.StringIO();writer=csv.writer(text,delimiter=delimiter)
        writer.writerow(HEADERS);writer.writerows(rows)
        return '\ufeff'+text.getvalue()

    def test_native_headers_ranges_multiplatform_history(self):
        rows=[['demo','FI','Finland','Demo','Yes','2026-12','TikTok + YouTube','PC, gaming','106000.0','30K-70K','6K','<10K'],
              ['demo','FI','Finland','Demo','No','2026-13','YouTube','PC','106000','30K-70K','','']]
        for delimiter in [',',';']:
            result=import_csv(self.data(rows,delimiter),'collaborations.csv')
            self.assertEqual(result['count'],1)
            self.assertEqual(result['rowCount'],2)
            record=result['creators'][0]
            self.assertEqual(len(record['prenewHistory']),2)
            self.assertEqual(record['prenewHistory'][0]['TikTok views / video'],'<10K')
            self.assertIsNone(record['recentViews'])
            self.assertIsNone(record['sourceUrl'])
            self.assertIsNone(record['language'])
            self.assertEqual(record['followers'],106000)
            self.assertEqual(import_csv(self.data(rows,delimiter),'another.csv')['creators'][0]['id'],record['id'])

    def test_validation_atomic(self):
        row=['demo','FI','Finland','Demo','','','YouTube','PC','5000','','','']
        bad=row.copy();bad[8]='-3'
        with self.assertRaises(APIError):import_csv(self.data([row,bad]),'test.csv')
        self.assertIsNone(import_csv(self.data([row[:8]+['']+row[9:]]),'test.csv')['creators'][0]['followers'])
