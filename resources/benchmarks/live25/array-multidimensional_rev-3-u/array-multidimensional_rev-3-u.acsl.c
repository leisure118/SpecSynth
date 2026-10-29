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
	  loop assigns i, j, k, B[0 .. 999][0 .. 999][0 .. 999];
	  loop variant n - i;
	*/
	while(i < n){
		j=0;
		k=0;
		/*@
		  loop invariant 0 <= j <= n;
		  loop assigns j, k, B[i][0 .. 999][0 .. 999];
		  loop variant n - j;
		*/
		while(j < n){
			k=0;
			/*@
			  loop invariant 0 <= k <= n;
			  loop assigns k, B[i][j][0 .. 999];
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
	  loop invariant \forall integer ii, jj, kk; 0 <= ii < i && 0 <= jj < n && 0 <= kk < n ==> A[ii][jj][kk] == B[n-ii-1][n-jj-1][n-kk-1];
	  loop assigns i, j, k, A[0 .. 999][0 .. 999][0 .. 999];
	  loop variant n - i;
	*/
	while(i < n){
		j=0;
		k=0;
		/*@
		  loop invariant 0 <= j <= n;
		  loop invariant \forall integer jj, kk; 0 <= jj < j && 0 <= kk < n ==> A[i][jj][kk] == B[n-i-1][n-jj-1][n-kk-1];
		  loop assigns j, k, A[i][0 .. 999][0 .. 999];
		  loop variant n - j;
		*/
		while(j < n){
			k=0;
			/*@
			  loop invariant 0 <= k <= n;
			  loop invariant \forall integer kk; 0 <= kk < k ==> A[i][j][kk] == B[n-i-1][n-j-1][n-kk-1];
			  loop assigns k, A[i][j][0 .. 999];
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
	  loop invariant \forall integer ii, jj, kk; 0 <= ii < n && 0 <= jj < n && 0 <= kk < n ==> A[ii][jj][kk] == B[n-ii-1][n-jj-1][n-kk-1];
	  loop assigns i, j, k;
	  loop variant n - i;
	*/
	while(i < n){
		j=0;
		k=0;
		/*@
		  loop invariant 0 <= j <= n;
		  loop invariant \forall integer ii, jj, kk; 0 <= ii < n && 0 <= jj < n && 0 <= kk < n ==> A[ii][jj][kk] == B[n-ii-1][n-jj-1][n-kk-1];
		  loop assigns j, k;
		  loop variant n - j;
		*/
		while(j < n){
			k=0;
			/*@
			  loop invariant 0 <= k <= n;
			  loop invariant \forall integer ii, jj, kk; 0 <= ii < n && 0 <= jj < n && 0 <= kk < n ==> A[ii][jj][kk] == B[n-ii-1][n-jj-1][n-kk-1];
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
