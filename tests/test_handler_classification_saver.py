# Copyright 2020 MONAI Consortium
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import csv
import shutil
import unittest
import numpy as np
import torch
from ignite.engine import Engine

from monai.handlers.classification_saver import ClassificationSaver


class TestHandlerClassificationSaver(unittest.TestCase):

    def test_saved_content(self):
        default_dir = os.path.join('.', 'tempdir')
        shutil.rmtree(default_dir, ignore_errors=True)

        # set up engine
        def _train_func(engine, batch):
            return torch.zeros(8)

        engine = Engine(_train_func)

        # set up testing handler
        saver = ClassificationSaver(output_dir=default_dir)
        saver.attach(engine)

        data = [{'filename_or_obj': ['testfile' + str(i) for i in range(8)]}]
        engine.run(data, epoch_length=2, max_epochs=1)
        filepath = os.path.join(default_dir, 'predictions.csv')
        self.assertTrue(os.path.exists(filepath))
        with open(filepath, 'r') as f:
            reader = csv.reader(f)
            i = 0
            for row in reader:
                self.assertEqual(row[0], 'testfile' + str(i))
                self.assertEqual(np.array(row[1:]).astype(np.float32), 0.0)
                i += 1
            self.assertEqual(i, 8)
        shutil.rmtree(default_dir)


if __name__ == '__main__':
    unittest.main()
