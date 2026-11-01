#include <assert.h>

/*@ axiomatic Parity {
  axiom odd_mod2: \forall integer k; (2*k + 1) % 2 == 1;
} */

/*@ assigns \nothing; */
int unknown1();
/*@ assigns \nothing; */
int unknown2();
/*@ assigns \nothing; */
int unknown3();
/*@ assigns \nothing; */
int unknown4();

int main()
{
	int i = 1;
	int j = 0;
	int z = i - j;
	int x = 0;
	int y = 0;
	int w = 0;

	/*@
	  loop invariant x == y;
	  loop invariant w == 2*y;
	  loop invariant \exists integer k; z == 2*k + 1;
	  loop assigns z, x, y, w;
	*/
	while(unknown2())
	{
		z += x + y + w;
		y++;
		if (z % 2 == 1)
		  x++;
		w += 2;
	}

	//@ assert(x==y);
}
