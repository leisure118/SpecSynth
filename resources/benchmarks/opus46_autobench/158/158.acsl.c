#include <assert.h>
/*@ assigns \nothing; */
int unknown1();
/*@ assigns \nothing; */
int unknown2();
/*@ assigns \nothing; */
int unknown3();
/*@ assigns \nothing; */
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
    loop invariant i >= 0;
    loop invariant j >= 0;
    loop assigns x, y, i, j;
  */
  while(unknown1())
  {
    /*@
      loop invariant x == y;
      loop invariant i >= j;
      loop invariant i >= 0;
      loop invariant j >= 0;
      loop assigns i, j;
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
