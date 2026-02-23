
import unittest
from chattool.utils import mask_secret
from chattool.config.elements import EnvField

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
        f2.value = "secret" # length 6 -> s****t
        self.assertEqual(f2.mask_value(), "s****t")
        
        f3 = EnvField("KEY", is_sensitive=True)
        f3.value = "longsecretkey" # length 13 -> lo*ey
        # 7 <= 13 <= 14: api_key[:2] + '*' * (length - 4) + api_key[-2:]
        # lo + * * 9 + ey
        self.assertEqual(f3.mask_value(), "lo*********ey")

if __name__ == '__main__':
    unittest.main()
