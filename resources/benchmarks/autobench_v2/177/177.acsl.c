#include <assert.h>
int unknown1();
int unknown2();
int unknown3();
int unknown4();

/*
 * Adapted from ex20 from NECLA Static Analysis Benchmarks
 */

void foo(int k, int flag)
{
  int i=0;
  int j=0;
  int n;
  int __BLAST_NONDET;

  if (flag == 1){
     n=1;
  } else {
     n=2;
  }

  i=0;

  /*@
    loop invariant 0 <= i;
    loop invariant i <= k+1 || k < 0;
    loop invariant j == i * n;
    loop assigns i, j;
    loop variant k+1 - i;
  */
  while ( i <= k) {
    i++;
    j = j + n;
  }
  if(flag == 1) {
    //@ assert(j == i);
  }
	
}


