"""
Signature algorithms for Douyin API requests.
Based on f2 library's XBogus implementation.
"""
import time
import base64
import hashlib
import random
import string


class XBogus:
    """X-Bogus signature generator for Douyin API."""

    def __init__(self, user_agent: str = "") -> None:
        self.Array = [
            None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None,
            None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None,
            None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None,
            0, 1, 2, 3, 4, 5, 6, 7, 8, 9, None, None, None, None, None, None, None, None, None, None, None,
            None, None, None, None, None, None, None, None, None, None, None, None, None, None, None, None,
            None, None, None, None, None, None, None, None, None, None, None, None, 10, 11, 12, 13, 14, 15
        ]
        self.character = "Dkdpgh4ZKsQB80/Mfvw36XI1R25-WUAlEi7NLboqYTOPuzmFjJnryx9HVGcaStCe="
        self.ua_key = b"\x00\x01\x0c"
        self.user_agent = (
            user_agent
            if user_agent
            else "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )

    def md5_str_to_array(self, md5_str):
        """Convert a string to an array of integers using md5."""
        if isinstance(md5_str, str) and len(md5_str) > 32:
            return [ord(char) for char in md5_str]
        else:
            array = []
            idx = 0
            while idx < len(md5_str):
                array.append(
                    (self.Array[ord(md5_str[idx])] << 4)
                    | self.Array[ord(md5_str[idx + 1])]
                )
                idx += 2
            return array

    def md5_encrypt(self, url_params):
        """Encrypt the URL path using multiple rounds of md5 hashing."""
        hashed_url_params = self.md5_str_to_array(
            self.md5(self.md5_str_to_array(self.md5(url_params)))
        )
        return hashed_url_params

    def md5(self, input_data):
        """Calculate the md5 hash value of the input data."""
        if isinstance(input_data, str):
            array = self.md5_str_to_array(input_data)
        elif isinstance(input_data, list):
            array = input_data
        else:
            raise ValueError("Invalid input type. Expected str or list.")

        md5_hash = hashlib.md5()
        md5_hash.update(bytes(array))
        return md5_hash.hexdigest()

    def encoding_conversion(
        self, a, b, c, e, d, t, f, r, n, o, i, _, x, u, s, l, v, h, p
    ):
        """First encoding conversion."""
        y = [a]
        y.append(int(i))
        y.extend([b, _, c, x, e, u, d, s, t, l, f, v, r, h, n, p, o])
        re = bytes(y).decode("ISO-8859-1")
        return re

    def encoding_conversion2(self, a, b, c):
        """Second encoding conversion."""
        return chr(a) + chr(b) + c

    def rc4_encrypt(self, key, data):
        """Encrypt data using the RC4 algorithm."""
        S = list(range(256))
        j = 0
        encrypted_data = bytearray()

        for i in range(256):
            j = (j + S[i] + key[i % len(key)]) % 256
            S[i], S[j] = S[j], S[i]

        i = j = 0
        for byte in data:
            i = (i + 1) % 256
            j = (j + S[i]) % 256
            S[i], S[j] = S[j], S[i]
            encrypted_byte = byte ^ S[(S[i] + S[j]) % 256]
            encrypted_data.append(encrypted_byte)

        return encrypted_data

    def calculation(self, a1, a2, a3):
        """Perform bitwise calculation."""
        x1 = (a1 & 255) << 16
        x2 = (a2 & 255) << 8
        x3 = x1 | x2 | a3
        return (
            self.character[(x3 & 16515072) >> 18]
            + self.character[(x3 & 258048) >> 12]
            + self.character[(x3 & 4032) >> 6]
            + self.character[x3 & 63]
        )

    def get_xbogus(self, url_params: str) -> tuple:
        """
        Get the X-Bogus value for the given URL parameters.

        Returns:
            tuple: (full_params_with_xbogus, xbogus_value, user_agent)
        """
        array1 = self.md5_str_to_array(
            self.md5(
                base64.b64encode(
                    self.rc4_encrypt(self.ua_key, self.user_agent.encode("ISO-8859-1"))
                ).decode("ISO-8859-1")
            )
        )

        array2 = self.md5_str_to_array(
            self.md5(self.md5_str_to_array("d41d8cd98f00b204e9800998ecf8427e"))
        )
        url_params_array = self.md5_encrypt(url_params)

        timer = int(time.time())
        ct = 536919696
        array3 = []
        array4 = []
        xb_ = ""

        new_array = [
            64, 0.00390625, 1, 12,
            url_params_array[14], url_params_array[15], array2[14], array2[15], array1[14], array1[15],
            timer >> 24 & 255, timer >> 16 & 255, timer >> 8 & 255, timer & 255,
            ct >> 24 & 255, ct >> 16 & 255, ct >> 8 & 255, ct & 255
        ]

        xor_result = new_array[0]
        for i in range(1, len(new_array)):
            b = new_array[i]
            if isinstance(b, float):
                b = int(b)
            xor_result ^= b

        new_array.append(xor_result)

        idx = 0
        while idx < len(new_array):
            array3.append(new_array[idx])
            try:
                array4.append(new_array[idx + 1])
            except IndexError:
                pass
            idx += 2

        merge_array = array3 + array4

        garbled_code = self.encoding_conversion2(
            2,
            255,
            self.rc4_encrypt(
                "ÿ".encode("ISO-8859-1"),
                self.encoding_conversion(*merge_array).encode("ISO-8859-1"),
            ).decode("ISO-8859-1"),
        )

        idx = 0
        while idx < len(garbled_code):
            xb_ += self.calculation(
                ord(garbled_code[idx]),
                ord(garbled_code[idx + 1]),
                ord(garbled_code[idx + 2]),
            )
            idx += 3

        params = f"{url_params}&X-Bogus={xb_}"
        return (params, xb_, self.user_agent)


class SignatureManager:
    """Manager for generating various signatures."""

    def __init__(self, user_agent: str = ""):
        self.xbogus = XBogus(user_agent)
        self.user_agent = user_agent or self.xbogus.user_agent

    def sign_url(self, base_url: str, params: dict) -> str:
        """
        Sign URL parameters with X-Bogus.

        Args:
            base_url: The base API URL
            params: Dictionary of URL parameters

        Returns:
            Signed URL with X-Bogus parameter
        """
        from urllib.parse import urlencode
        query_string = urlencode(params)
        signed_params, _, _ = self.xbogus.get_xbogus(query_string)
        return f"{base_url}?{signed_params}"

    @staticmethod
    def gen_random_str(length: int = 16) -> str:
        """Generate a random string."""
        return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

    @staticmethod
    def gen_mstoken(length: int = 128) -> str:
        """Generate a random msToken."""
        chars = string.ascii_letters + string.digits + '_-'
        return ''.join(random.choices(chars, k=length))

    @staticmethod
    def gen_webid() -> str:
        """Generate a random webid."""
        return str(random.randint(7000000000000000000, 7999999999999999999))

    @staticmethod
    def get_timestamp() -> int:
        """Get current timestamp in milliseconds."""
        return int(time.time() * 1000)
