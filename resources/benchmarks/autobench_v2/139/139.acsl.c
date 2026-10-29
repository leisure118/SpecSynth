#include <assert.h>
int unknown1();
int unknown2();
int unknown3();
int unknown4();

void main()
{


  int w = 1;
  int z = 0;
  int x = 0;
  int y = 0;

  /*@
    loop invariant x == y;
    loop invariant x >= 0;
    loop invariant y >= 0;
    loop invariant z >= 0;
    loop invariant w == z + 1;
    loop assigns x, y, z, w;
  */
  while(unknown1()) {
	  
    /*@
      loop invariant x >= 0;
      loop invariant y >= 0;
      loop invariant z >= 0;
      loop invariant (w % 2 == 1) <==> (z % 2 == 0);
      loop invariant \at(x, LoopEntry) - \at(y, LoopEntry) == x - y;
      loop assigns x, y;
    */
    while(unknown2()){
      if(w%2 == 1) x++;
      if(z%2 == 0) y++;
    }
    z = x + y;
    w = z + 1;
  }

  
  //@ assert(x == y);
}
