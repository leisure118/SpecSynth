#include <assert.h>
int unknown1();
int unknown2();
int unknown3();
int unknown4();

void main() {


  int w = 1;
  int z = 0;
  int x = 0;
  int y = 0;

  /*@
    loop invariant 0 <= w <= 1;
    loop invariant 0 <= z <= 1;
    loop invariant w != z;
    loop invariant x == y;
    loop assigns w, z, x, y;
  */
  while(unknown2()){
  	if(w) {
  	  x++;
  	  w = !w;
	  }
	
    if(!z) {
      y++; 
      z=!z;
    }
  }

  //@ assert(x==y);
  
}
