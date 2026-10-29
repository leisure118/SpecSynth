#include<limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();
int main()
{
	int i,j;
	int m=1000,n=1500;
	int A [1000][1500];
	int C=unknown();
	i=0;
	j=0;
	/*@
	  loop invariant 0 <= i <= m;
	  loop invariant \forall integer p, q; 0 <= p < i && 0 <= q < n ==> A[p][q] == C;
	  loop assigns i, j, A[0 .. m-1][0 .. n-1];
	  loop variant m - i;
	*/
	while(i < m){
		j=0;
		/*@
		  loop invariant 0 <= j <= n;
		  loop invariant \forall integer k; 0 <= k < j ==> A[i][k] == C;
		  loop assigns j, A[i][0 .. n-1];
		  loop variant n - j;
		*/
		while(j < n){
                        A[i][j]=C;
			j=j+1;
		}
		i=i+1;
    }
	i=0;
	j=0;
	/*@
	  loop invariant 0 <= i <= m;
	  loop invariant \forall integer p, q; 0 <= p < m && 0 <= q < n ==> A[p][q] == C;
	  loop assigns i, j;
	  loop variant m - i;
	*/
	while(i < m){
		j=0;
		/*@
		  loop invariant 0 <= j <= n;
		  loop invariant \forall integer p, q; 0 <= p < m && 0 <= q < n ==> A[p][q] == C;
		  loop assigns j;
		  loop variant n - j;
		*/
		while(j < n){
                        //@ assert(A[i][j]==C);
			j=j+1;
		}
		i=i+1;
    }
return 0;
}
