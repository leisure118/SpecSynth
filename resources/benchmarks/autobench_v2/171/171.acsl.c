#include <assert.h>
int unknown1();
int unknown2();
int unknown3();
int unknown4();

/*@
  requires n >= 0;
*/
void foo(int n)
{
  int x=0;
  int y=0;
  int i=0;
  
  /*@
    loop invariant 0 <= i <= n;
    loop invariant x == i;
    loop invariant y == i / 2;
    loop assigns i, x, y;
    loop variant n - i;
  */
  while(i<n) {
    i++;
    x++;
    if(i%2 == 0) y++;
  }
  
  if(i%2 == 0) {
    //@ assert(x==2*y);
  }
}

