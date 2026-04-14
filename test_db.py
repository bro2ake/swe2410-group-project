import unittest
import os
from databaseConnect import DatabaseManager

class TestDatabase(unittest.TestCase):
    def setUp(self):
        # Create a fresh database for every test
        self.db = DatabaseManager("test_temp.db")

    def tearDown(self):
        # Delete the test database after the test is done
        if os.path.exists("test_temp.db"):
            os.remove("test_temp.db")

    def test_add_and_get_user(self):
        self.db.add_user("jackson", "secret_hash")
        result = self.db.get_hash("jackson")
        self.assertEqual(result, "secret_hash") # This "Asserts" that the test passed

if __name__ == "__main__":
    unittest.main()