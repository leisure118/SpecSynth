#include <limits.h>
/*@
    ensures \result >= INT_MIN && \result <= INT_MAX;
*/
int unknown_int();


int __BLAST_NONDET;

int main() {
    int i,j,k,n,l,m;

    n = unknown_int();
    m = unknown_int();
    l = unknown_int();
    if(3*n<=m+l); else goto END;
    /*@
      loop invariant 0 <= i;
      loop assigns i, j, k;
      loop variant n - i;
    */
    for (i=0;i<n;i++)
        /*@
          loop invariant 2*i <= j;
          loop assigns j, k;
          loop variant 3*i - j;
        */
        for (j = 2*i;j<3*i;j++)
            /*@
              loop invariant i <= k;
              loop assigns k;
              loop variant j - k;
            */
            for (k = i; k< j; k++)
                //@ assert( k-i <= 2*n );
END:
    return 0;
}