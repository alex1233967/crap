#!/usr/bin/env python
'''
#include <stdio.h>#define KEY_LENGTH 2 // Can be anything from 1 to 13

main(){
  unsigned char ch;
  FILE *fpIn, *fpOut;
  int i;  unsigned char key[KEY_LENGTH] = {0x00, 0x00};
  /* of course, I did not use the all-0s key to encrypt */

  fpIn = fopen("ptext.txt", "r");
  fpOut = fopen("ctext.txt", "w");
  i=0;
  while (fscanf(fpIn, "%c", &ch) != EOF) {
    /* avoid encrypting newline characters */
   /* In a "real-world" implementation of the Vigenere cipher,
      every ASCII character in the plaintext would be encrypted.
      However, I want to avoid encrypting newlines here because
      it makes recovering the plaintext slightly more difficult... */
   /* ...and my goal is not to create "production-quality" code =) */
   if (ch!='\n') {
     fprintf(fpOut, "%02X", ch ^ key[i % KEY_LENGTH]); // ^ is logical XOR
     i++;      }
  }

  fclose(fpIn);
  fclose(fpOut);
  return;
}
'''
cipher = (
    "F96DE8C227A259C87EE1DA2AED57C93FE5DA36ED4EC87EF2C63AAE5B9A7EFFD673BE4ACF7"
    "BE8923CAB1ECE7AF2DA3DA44FCF7AE29235A24C963FF0DF3CA3599A70E5DA36BF1ECE77F8"
    "DC34BE129A6CF4D126BF5B9A7CFEDF3EB850D37CF0C63AA2509A76FF9227A55B9A6FE3D72"
    "0A850D97AB1DD35ED5FCE6BF0D138A84CC931B1F121B44ECE70F6C032BD56C33FF9D320ED"
    "5CDF7AFF9226BE5BDE3FF7DD21ED56CF71F5C036A94D963FF8D473A351CE3FE5DA3CB84DD"
    "B71F5C17FED51DC3FE8D732BF4D963FF3C727ED4AC87EF5DB27A451D47EFD9230BF47CA6B"
    "FEC12ABE4ADF72E29224A84CDF3FF5D720A459D47AF59232A35A9A7AE7D33FB85FCE7AF59"
    "23AA31EDB3FF7D33ABF52C33FF0D673A551D93FFCD33DA35BC831B1F43CBF1EDF67F0DF23"
    "A15B963FE5DA36ED68D378F4DC36BF5B9A7AFFD121B44ECE76FEDC73BE5DD27AFCD773BA5"
    "FC93FE5DA3CB859D26BB1C63CED5CDF3FE2D730B84CDF3FF7DD21ED5ADF7CF0D636BE1EDB"
    "79E5D721ED57CE3FE6D320ED57D469F4DC27A85A963FF3C727ED49DF3FFFDD24ED55D470E"
    "69E73AC50DE3FE5DA3ABE1EDF67F4C030A44DDF3FF5D73EA250C96BE3D327A84D963FE5DA"
    "32B91ED36BB1D132A31ED87AB1D021A255DF71B1C436BF479A7AF0C13AA14794"
)


def decrypt_vigenere(ciphertext, freq):
    N = find_key_length(ciphertext)
    plaintext_streams = []
    ciphertext_streams = [ciphertext[i::N] for i in range(0, N)]

    for stream in ciphertext_streams:
        possible_plaintexts = []

        for b1 in range(0, 256):
            plaintext = ''

            for b2 in stream:
                c = b1 ^ b2
                if (32 <= c < 127):
                    plaintext += chr(c)
                else:
                    break

            if len(stream) == len(plaintext):
                possible_plaintexts.append(plaintext)

        plaintext_streams.append(best_plaintext(possible_plaintexts, freq))

    plaintext = ''.join([''.join(i) for i in zip(*plaintext_streams)])
    return plaintext


def best_plaintext(possible_plaintexts, freq):
    index_of_coincidence = 0.065
    maximum = 0

    for text in possible_plaintexts:
        text_index = 0

        for k, v in freq_table(text).items():
            if k in freq.keys():
                text_index += freq[k] * v

        if text_index > maximum:
            maximum = text_index
            best_text = text

    return best_text


def freq_table(text):
    freq = {}
    for c in set(text):
        freq[c] = text.count(c) / len(text)
    return freq


def find_key_length(ciphertext, start=1, end=13):
    length = start
    maximum = 0
    for i in range(start, end + 1):
        coef = sum([v*v for v in freq_table(ciphertext[::i]).values()])
        if coef > maximum:
            maximum = coef
            length = i
    return length


if __name__ == "__main__":
    ciphertext = bytes.fromhex(cipher)

    with open(r"alice_in_wonderland.txt", 'r') as f:
        text_sample = f.read()

    text_sample_freq = freq_table(text_sample)

    plaintext = decrypt_vigenere(ciphertext, text_sample_freq)
    print(plaintext)
