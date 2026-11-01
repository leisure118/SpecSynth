#include <assert.h>
/*@ assigns \nothing; */
int unknown1();
/*@ assigns \nothing; */
int unknown2();
/*@ assigns \nothing; */
int unknown3();
/*@ assigns \nothing; */
int unknown4();

/*@
requires n > 0;
requires n < 10;
*/
void foo(int n) {
  int c1 = 4000;
  int c2 = 2000;
  int v;
  int i, k, j;
  k = 0;
  i = 0;
  /*@
    loop invariant 0 <= i <= n;
    loop invariant k >= i * 2000;
    loop invariant k <= i * 4000;
    loop assigns i, k, v;
    loop variant n - i;
  */
  while( i < n ) {
    i++;
    if(unknown2() % 2 == 0)
      v = 0;
    else v = 1;

    if( v == 0 )
      k += c1;
    else
      k += c2;
  }

  //@ assert(k > n);
}

