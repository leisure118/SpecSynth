#include<limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();
int main()
{
	int i,j,k;
	int n=1000;
	int A [1000][1000][1000];
        int B [1000][1000][1000];
	i=0;
	j=0;
	k=0;
	/*@
	  loop invariant 0 <= i <= n;
	  loop assigns i, j, k, B[0..n-1][0..n-1][0..n-1];
	  loop variant n - i;
	*/
	while(i < n){
		j=0;
		k=0;
		/*@
		  loop invariant 0 <= j <= n;
		  loop assigns j, k, B[i][0..n-1][0..n-1];
		  loop variant n - j;
		*/
		while(j < n){
			k=0;
			/*@
			  loop invariant 0 <= k <= n;
			  loop assigns k, B[i][j][0..n-1];
			  loop variant n - k;
			*/
			while(k < n){
                                B[i][j][k]= unknown();
				k=k+1;
			}
			j=j+1;
		}
		i=i+1;
    }
	i=0;
	j=0;
	k=0;
	/*@
	  loop invariant 0 <= i <= n;
	  loop invariant \forall integer i2, j2, k2; 0 <= i2 < i && 0 <= j2 < n && 0 <= k2 < n ==> A[i2][j2][k2] == B[n-1-i2][n-1-j2][n-1-k2];
	  loop assigns i, j, k, A[0..n-1][0..n-1][0..n-1];
	  loop variant n - i;
	*/
	while(i < n){
		j=0;
		k=0;
		/*@
		  loop invariant 0 <= j <= n;
		  loop invariant \forall integer i2, j2, k2; 0 <= i2 < i && 0 <= j2 < n && 0 <= k2 < n ==> A[i2][j2][k2] == B[n-1-i2][n-1-j2][n-1-k2];
		  loop invariant \forall integer j2, k2; 0 <= j2 < j && 0 <= k2 < n ==> A[i][j2][k2] == B[n-1-i][n-1-j2][n-1-k2];
		  loop assigns j, k, A[i][0..n-1][0..n-1];
		  loop variant n - j;
		*/
		while(j < n){
			k=0;
			/*@
			  loop invariant 0 <= k <= n;
			  loop invariant \forall integer i2, j2, k2; 0 <= i2 < i && 0 <= j2 < n && 0 <= k2 < n ==> A[i2][j2][k2] == B[n-1-i2][n-1-j2][n-1-k2];
			  loop invariant \forall integer j2, k2; 0 <= j2 < j && 0 <= k2 < n ==> A[i][j2][k2] == B[n-1-i][n-1-j2][n-1-k2];
			  loop invariant \forall integer k2; 0 <= k2 < k ==> A[i][j][k2] == B[n-1-i][n-1-j][n-1-k2];
			  loop assigns k, A[i][j][0..n-1];
			  loop variant n - k;
			*/
			while(k < n){
					A[i][j][k]=B[n-i-1][n-j-1][n-k-1];
					k=k+1;
			}
			j=j+1;
		}
		i=i+1;
    }
	i=0;
	j=0;
	k=0;
	/*@
	  loop invariant 0 <= i <= n;
	  loop invariant \forall integer i2, j2, k2; 0 <= i2 < n && 0 <= j2 < n && 0 <= k2 < n ==> A[i2][j2][k2] == B[n-1-i2][n-1-j2][n-1-k2];
	  loop assigns i, j, k;
	  loop variant n - i;
	*/
	while(i < n){
		j=0;
		k=0;
		/*@
		  loop invariant 0 <= j <= n;
		  loop invariant \forall integer i2, j2, k2; 0 <= i2 < n && 0 <= j2 < n && 0 <= k2 < n ==> A[i2][j2][k2] == B[n-1-i2][n-1-j2][n-1-k2];
		  loop assigns j, k;
		  loop variant n - j;
		*/
		while(j < n){
			k=0;
			/*@
			  loop invariant 0 <= k <= n;
			  loop invariant \forall integer i2, j2, k2; 0 <= i2 < n && 0 <= j2 < n && 0 <= k2 < n ==> A[i2][j2][k2] == B[n-1-i2][n-1-j2][n-1-k2];
			  loop assigns k;
			  loop variant n - k;
			*/
			while(k < n){
					//@ assert(A[i][j][k]==B[n-i-1][n-j-1][n-k-1]);
					k=k+1;
			}
			j=j+1;
		}
		i=i+1;
    }
return 0;
}
