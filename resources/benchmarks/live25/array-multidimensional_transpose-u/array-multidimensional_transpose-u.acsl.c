#include<limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();
int main()
{
	int i;
	int k;
	int j;
	int n=1000;
        int m=1800;
	int A[1000][1000];
	int C[1000][1000];
	/*@
	  loop invariant 0 <= i <= n;
	  loop assigns i, j, A[0 .. n-1][0 .. n-1];
	  loop variant n - i;
	*/
	for ( i = 0 ; i < n ; i++ ){
          /*@
            loop invariant 0 <= j <= n;
            loop assigns j, A[i][0 .. n-1];
            loop variant n - j;
          */
          for ( j = 0 ; j < n ; j++ ){
                A[i][j]= unknown();
          }
    }
	i=0;
	j=0;
	/*@
	  loop invariant 0 <= i <= n;
	  loop invariant \forall integer p; 0 <= p < i ==> (\forall integer q; 0 <= q < n ==> C[q][p] == A[p][q]);
	  loop assigns i, j, C[0 .. n-1][0 .. n-1];
	  loop variant n - i;
	*/
	while(i < n){
		  j=0;
           /*@
             loop invariant 0 <= j <= n;
             loop invariant \forall integer q; 0 <= q < j ==> C[q][i] == A[i][q];
             loop assigns j, C[0 .. n-1][i];
             loop variant n - j;
           */
           while(j < n){
                C[j][i] = A[i][j];
		  		j=j+1;
          }
	i=i+1;
    }
	/*@
	  loop invariant 0 <= i <= n;
	  loop invariant \forall integer p, q; 0 <= p < n && 0 <= q < n ==> C[q][p] == A[p][q];
	  loop assigns i, j;
	  loop variant n - i;
	*/
	for ( i = 0 ; i < n ; i++ ){
          /*@
            loop invariant 0 <= j <= n;
            loop invariant \forall integer p, q; 0 <= p < n && 0 <= q < n ==> C[q][p] == A[p][q];
            loop assigns j;
            loop variant n - j;
          */
          for ( j = 0 ; j < n ; j++ ){
                //@ assert(C[j][i] == A[i][j]);
          }
    }
return 0;
}
