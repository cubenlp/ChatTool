
import unittest
from chattool.utils import mask_secret
from chattool.config import EnvField

class TestMaskValue(unittest.TestCase):
    def test_mask_secret(self):
        self.assertEqual(mask_secret(""), "")
        self.assertEqual(mask_secret("a"), "*")
        self.assertEqual(mask_secret("ab"), "**")
        self.assertEqual(mask_secret("abc"), "a*c")
        self.assertEqual(mask_secret("abcd"), "a**d")
        self.assertEqual(mask_secret("abcde"), "a***e")
        self.assertEqual(mask_secret("abcdef"), "a****f")
        self.assertEqual(mask_secret("abcdefg"), "ab***fg")
        self.assertEqual(mask_secret("abcdefgh"), "ab****gh")
        
    def test_env_field_mask_value(self):
        # Non-sensitive
        f1 = EnvField("KEY", is_sensitive=False)
        f1.value = "secret"
        self.assertEqual(f1.mask_value(), "secret")
        
        # Sensitive
        f2 = EnvField("KEY", is_sensitive=True)
        f2.value = "secret" # length 6 -> fully masked
        self.assertEqual(f2.mask_value(), "******")
        
        f3 = EnvField("KEY", is_sensitive=True)
        f3.value = "longsecretkey" # ChatEnv EnvField always fully masks sensitive values.
        self.assertEqual(f3.mask_value(), "*************")

if __name__ == '__main__':
    unittest.main()
