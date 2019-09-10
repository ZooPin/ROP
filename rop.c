#include <stdlib.h>
#include <stdio.h>

void vuln()
{
  char buffer[64];
  printf("Input: ");
  scanf("%s",buffer);
}
int main(int argc, char **argv)
{
  vuln();
}