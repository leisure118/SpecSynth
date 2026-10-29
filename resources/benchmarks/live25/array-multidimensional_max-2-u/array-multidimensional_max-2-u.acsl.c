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
	int max;
	i=0;
	j=0;
	/*@
	  loop invariant 0 <= i <= m;
	  loop assigns i, j, A[0 .. m-1][0 .. n-1];
	  loop variant m - i;
	*/
	while(i < m){
		j=0;
		/*@
		  loop invariant 0 <= j <= n;
		  loop assigns j, A[i][0 .. n-1];
		  loop variant n - j;
		*/
		while(j < n){
					A[i][j]=unknown();
			j=j+1;
		}
		i=i+1;
    }
	i=0;
	j=0;
        max=A [0][0];
	/*@
	  loop invariant 0 <= i <= n;
	  loop invariant \forall integer p; 0 <= p < i ==> \forall integer q; 0 <= q < n ==> A[p][q] <= max;
	  loop assigns i, j, max;
	  loop variant n - i;
	*/
	while(i < n){
		j=0;
		/*@
		  loop invariant 0 <= j <= n;
		  loop invariant \forall integer q; 0 <= q < j ==> A[i][q] <= max;
		  loop invariant max >= \at(max, LoopEntry);
		  loop assigns j, max;
		  loop variant n - j;
		*/
		while(j < n){
			if(A[i][j]>max){
                            max=A[i][j];
                        }
			j=j+1;
		}
			//@ assert \forall integer q; 0 <= q < n ==> A[i][q] <= max;
		i=i+1;
    }
	i=0;
	j=0;
	/*@
	  loop invariant 0 <= i <= n;
	  loop invariant \forall integer p; 0 <= p < i ==> \forall integer q; 0 <= q < n ==> A[p][q] <= max;
	  loop assigns i, j;
	  loop variant n - i;
	*/
	while(i < n){
		j=0;
		/*@
		  loop invariant 0 <= j <= n;
		  loop invariant \forall integer p; 0 <= p < i ==> \forall integer q; 0 <= q < n ==> A[p][q] <= max;
		  loop invariant \forall integer q; 0 <= q < j ==> A[i][q] <= max;
		  loop assigns j;
		  loop variant n - j;
		*/
		while(j < n){
			//@ assert(A[i][j]<=max);
			j=j+1;
		}
		i=i+1;
    }
return 0;
}
