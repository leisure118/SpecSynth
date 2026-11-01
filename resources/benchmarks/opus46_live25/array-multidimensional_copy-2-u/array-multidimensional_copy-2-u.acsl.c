#include<limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();
int main()
{
	int i,j;
	int n=1000;
	int A [1000][1000];
        int B [1000][1000];
	i=0;
	j=0;
	/*@
	  loop invariant 0 <= i <= n;
	  loop assigns i, j, B[0 .. n-1][0 .. n-1];
	  loop variant n - i;
	*/
	while(i < n){
		j=0;
		/*@
		  loop invariant 0 <= j <= n;
		  loop assigns j, B[i][0 .. n-1];
		  loop variant n - j;
		*/
		while(j < n){
					B[i][j]=unknown();
			j=j+1;
		}
		i=i+1;
    }
	i=0;
	j=0;
	/*@
	  loop invariant 0 <= i <= n;
	  loop invariant \forall integer p, q; 0 <= p < i && 0 <= q < n ==> A[p][q] == B[p][q];
	  loop assigns i, j, A[0 .. n-1][0 .. n-1];
	  loop variant n - i;
	*/
	while(i < n){
		j=0;
		/*@
		  loop invariant 0 <= j <= n;
		  loop invariant \forall integer q; 0 <= q < j ==> A[i][q] == B[i][q];
		  loop assigns j, A[i][0 .. n-1];
		  loop variant n - j;
		*/
		while(j < n){
					A[i][j]=B[i][j];
			j=j+1;
		}
		i=i+1;
    }
	i=0;
	j=0;
	/*@
	  loop invariant 0 <= i <= n;
	  loop invariant \forall integer p, q; 0 <= p < n && 0 <= q < n ==> A[p][q] == B[p][q];
	  loop assigns i, j;
	  loop variant n - i;
	*/
	while(i < n){
		j=0;
		/*@
		  loop invariant 0 <= j <= n;
		  loop invariant \forall integer p, q; 0 <= p < n && 0 <= q < n ==> A[p][q] == B[p][q];
		  loop assigns j;
		  loop variant n - j;
		*/
		while(j < n){
                            //@ assert(A[i][j]==B[i][j]);
			j=j+1;
		}
		i=i+1;
    }
return 0;
}
