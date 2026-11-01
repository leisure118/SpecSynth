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
	int p=500;
	int A [1000][1000][1000];
        int B [1000][1000][1000];
	//@ assert(p<n);
	i=0;
	j=0;
	k=0;
	/*@
	  loop invariant 0 <= i <= n;
	  loop assigns i, j, k, B[0 .. n-1][0 .. n-1][0 .. n-1];
	  loop variant n - i;
	*/
	while(i < n){
		j=0;
		k=0;
		/*@
		  loop invariant 0 <= j <= n;
		  loop assigns j, k, B[i][0 .. n-1][0 .. n-1];
		  loop variant n - j;
		*/
		while(j < n){
			k=0;
			/*@
			  loop invariant 0 <= k <= n;
			  loop assigns k, B[i][j][0 .. n-1];
			  loop variant n - k;
			*/
			while(k < n){
					B[i][j][k] = unknown();
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
	  loop invariant 0 <= i <= p;
	  loop invariant \forall integer ii, jj, kk; 0 <= ii < i && 0 <= jj < p && 0 <= kk < p ==> A[ii][jj][kk] == B[ii][jj][kk];
	  loop assigns i, j, k, A[0 .. p-1][0 .. p-1][0 .. p-1];
	  loop variant p - i;
	*/
	while(i < p){
		j=0;
		k=0;
		/*@
		  loop invariant 0 <= j <= p;
		  loop invariant \forall integer jj, kk; 0 <= jj < j && 0 <= kk < p ==> A[i][jj][kk] == B[i][jj][kk];
		  loop assigns j, k, A[i][0 .. p-1][0 .. p-1];
		  loop variant p - j;
		*/
		while(j < p){
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
		i=p;
		/*@
		  loop invariant p <= i <= n;
		  loop invariant \forall integer ii, jj, kk; p <= ii < i && p <= jj < n && p <= kk < n ==> A[ii][jj][kk] == B[ii][jj][kk];
		  loop assigns i, j, k, A[p .. n-1][p .. n-1][p .. n-1];
		  loop variant n - i;
		*/
		while(i < n){
		j=p;
		/*@
		  loop invariant p <= j <= n;
		  loop invariant \forall integer jj, kk; p <= jj < j && p <= kk < n ==> A[i][jj][kk] == B[i][jj][kk];
		  loop assigns j, k, A[i][p .. n-1][p .. n-1];
		  loop variant n - j;
		*/
		while(j < n){
			k=p;
			/*@
			  loop invariant p <= k <= n;
			  loop invariant \forall integer kk; p <= kk < k ==> A[i][j][kk] == B[i][j][kk];
			  loop assigns k, A[i][j][p .. n-1];
			  loop variant n - k;
			*/
			while(k < n){
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
	  loop invariant 0 <= i <= n;
	  loop invariant \forall integer ii, jj, kk; 0 <= ii < p && 0 <= jj < p && 0 <= kk < p ==> A[ii][jj][kk] == B[ii][jj][kk];
	  loop invariant \forall integer ii, jj, kk; p <= ii < n && p <= jj < n && p <= kk < n ==> A[ii][jj][kk] == B[ii][jj][kk];
	  loop assigns i, j, k;
	  loop variant n - i;
	*/
	while(i < n){
		j=0;
		k=0;
		/*@
		  loop invariant 0 <= j <= n;
		  loop invariant \forall integer ii, jj, kk; 0 <= ii < p && 0 <= jj < p && 0 <= kk < p ==> A[ii][jj][kk] == B[ii][jj][kk];
		  loop invariant \forall integer ii, jj, kk; p <= ii < n && p <= jj < n && p <= kk < n ==> A[ii][jj][kk] == B[ii][jj][kk];
		  loop assigns j, k;
		  loop variant n - j;
		*/
		while(j < n){
			k=0;
			/*@
			  loop invariant 0 <= k <= n;
			  loop invariant \forall integer ii, jj, kk; 0 <= ii < p && 0 <= jj < p && 0 <= kk < p ==> A[ii][jj][kk] == B[ii][jj][kk];
			  loop invariant \forall integer ii, jj, kk; p <= ii < n && p <= jj < n && p <= kk < n ==> A[ii][jj][kk] == B[ii][jj][kk];
			  loop assigns k;
			  loop variant n - k;
			*/
			while(k < n){
					//@ assert(A[i][j][k]==B[i][j][k]);
					k=k+1;
			}
			j=j+1;
		}
		i=i+1;
    }
return 0;
}
