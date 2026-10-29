#include<limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();
int main()
{
	int i,j,k;
	int m=1000,n=1500,p=1800;
	int A [1000][1500][1800];
	int B [1000][1500][1800];
	i=0;
	j=0;
	k=0;
	/*@
	  loop invariant 0 <= i <= m;
	  loop assigns i, j, k, B[0 .. m-1][0 .. n-1][0 .. p-1];
	  loop variant m - i;
	*/
	while(i < m){
		j=0;
		k=0;
		/*@
		  loop invariant 0 <= j <= n;
		  loop assigns j, k, B[i][0 .. n-1][0 .. p-1];
		  loop variant n - j;
		*/
		while(j < n){
			k=0;
			/*@
			  loop invariant 0 <= k <= p;
			  loop assigns k, B[i][j][0 .. p-1];
			  loop variant p - k;
			*/
			while(k < p){
					B[i][j][k]=unknown();
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
	  loop invariant 0 <= i <= m;
	  loop invariant \forall integer ii, jj, kk; 0 <= ii < i && 0 <= jj < n && 0 <= kk < p ==> A[ii][jj][kk] == B[ii][jj][kk];
	  loop assigns i, j, k, A[0 .. m-1][0 .. n-1][0 .. p-1];
	  loop variant m - i;
	*/
	while(i < m){
		j=0;
		k=0;
		/*@
		  loop invariant 0 <= j <= n;
		  loop invariant \forall integer jj, kk; 0 <= jj < j && 0 <= kk < p ==> A[i][jj][kk] == B[i][jj][kk];
		  loop assigns j, k, A[i][0 .. n-1][0 .. p-1];
		  loop variant n - j;
		*/
		while(j < n){
			k=0;
			/*@
			  loop invariant 0 <= k <= p;
			  loop invariant \forall integer kk; 0 <= kk < k ==> A[i][j][kk] == B[i][j][kk];
			  loop assigns k, A[i][j][0 .. p-1];
			  loop variant p - k;
			*/
			while(k < p){
					A[i][j][k]=B[i][j][k];
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
	  loop invariant 0 <= i <= m;
	  loop invariant \forall integer ii, jj, kk; 0 <= ii < i && 0 <= jj < n && 0 <= kk < p ==> A[ii][jj][kk] == B[ii][jj][kk];
	  loop assigns i, j, k;
	  loop variant m - i;
	*/
	while(i < m){
		j=0;
		k=0;
		/*@
		  loop invariant 0 <= j <= n;
		  loop invariant \forall integer jj, kk; 0 <= jj < j && 0 <= kk < p ==> A[i][jj][kk] == B[i][jj][kk];
		  loop assigns j, k;
		  loop variant n - j;
		*/
		while(j < n){
			k=0;
			/*@
			  loop invariant 0 <= k <= p;
			  loop invariant \forall integer kk; 0 <= kk < k ==> A[i][j][kk] == B[i][j][kk];
			  loop assigns k;
			  loop variant p - k;
			*/
			while(k < p){
					//@ assert(A[i][j][k]==B[i][j][k]);
					k=k+1;
			}
			j=j+1;
		}
		i=i+1;
    }
return 0;
}
