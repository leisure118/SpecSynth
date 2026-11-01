#include <stdio.h>

/*@ assigns \nothing; ensures \result == 1; */
int power(int x);

/*@ assigns \nothing; ensures \result == 1; */
int factorial(int x);

/*@
  requires n >= 2;
  assigns \nothing;
  ensures \result == 1;
*/
int pdt(int n) {
  int prod = 1;
  int i = 2;

  /*@
    loop invariant 2 <= i <= n + 1;
    loop invariant prod == 1;
    loop assigns prod, i;
    loop variant n - i;
  */
  while(i < n) {
    prod = power(i/2)*factorial(i/2);
    i = i+2;
  }
  return prod;
}

int main() {
    int p = pdt(10);
    //@ assert p == 1;
}
