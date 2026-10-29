#include <assert.h>
int unknown1();
int unknown2();
int unknown3();
int unknown4();

void main(int flag)
{

	int x = 0;
	int y = 0;

	int j = 0;
	int i = 0;

	/*@
	  loop invariant 0 <= x;
	  loop invariant x == y;
	  loop invariant j - i == (flag != 0 ? 1 : 0) * x;
	  loop assigns i, j, x, y;
	*/
	while(unknown1())
	{
	  x++;
	  y++;
	  i += x;
	  j += y;
	  if (flag)
	  	j+=1;
	} 
	//@ assert(j>=i);
	
}
