#include <assert.h>
int unknown1();
int unknown2();
int unknown3();
int unknown4();

void main()
{
  int x = 0;
  int y = 0;
  int i = 0;
  int j = 0;

  /*@
    loop invariant x == y;
    loop invariant i >= j;
    loop assigns x, y, i, j;
    loop variant 2147483647 - x;
  */
  while(unknown1())
  {
    /*@
      loop invariant x == y;
      loop invariant i >= \at(i, LoopEntry);
      loop invariant j == \at(j, LoopEntry);
      loop assigns i, j;
      loop variant 2147483647 - i;
    */
    while(unknown2())
    {
       if(x == y)
          i++;
       else
          j++;
    }
    if(i >= j)
    {
       x++;
       y++;
    }
    else
       y++;
  }

  //@ assert(i >= j);
}
