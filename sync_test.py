import unittest
import sync
import os
import sys

class SyncTests(unittest.TestCase):
    def test_get_newcam_list(self):
        newcam_list = sync.get_newcam_list('./testdata')
        self.assertEqual(len(newcam_list), 2)
        self.assertEqual(os.path.isfile(sync.CHECKPOINT), True)
        f = open(sync.CHECKPOINT, 'r')
        str_time = f.readline()
        f.close()
        self.assertEqual(str_time, '2020-04-27_15-27-53')


if __name__ == '__main__':
    unittest.main()