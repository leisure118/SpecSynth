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
	  loop invariant \forall integer ii; 0 <= ii < i ==> (\forall integer jj; 0 <= jj < p ==> (\forall integer kk; 0 <= kk < p ==> A[ii][jj][kk] == B[ii][jj][kk]));
	  loop assigns i, j, k, A[0 .. 499][0 .. 499][0 .. 499];
	  loop variant p - i;
	*/
	while(i < p){
		j=0;
		k=0;
		/*@
		  loop invariant 0 <= j <= p;
		  loop invariant \forall integer jj; 0 <= jj < j ==> (\forall integer kk; 0 <= kk < p ==> A[i][jj][kk] == B[i][jj][kk]);
		  loop assigns j, k, A[i][0 .. 499][0 .. 499];
		  loop variant p - j;
		*/
		while(j < p){
			k=0;
			/*@
			  loop invariant 0 <= k <= p;
			  loop invariant \forall integer kk; 0 <= kk < k ==> A[i][j][kk] == B[i][j][kk];
			  loop assigns k, A[i][j][0 .. 499];
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
		  loop invariant \forall integer ii; 0 <= ii < p ==> (\forall integer jj; 0 <= jj < p ==> (\forall integer kk; 0 <= kk < p ==> A[ii][jj][kk] == B[ii][jj][kk]));
		  loop invariant \forall integer ii; p <= ii < i ==> (\forall integer jj; p <= jj < n ==> (\forall integer kk; p <= kk < n ==> A[ii][jj][kk] == B[ii][jj][kk]));
		  loop assigns i, j, k, A[500 .. 999][500 .. 999][500 .. 999];
		  loop variant n - i;
		*/
		while(i < n){
		j=p;
		/*@
		  loop invariant p <= j <= n;
		  loop invariant \forall integer jj; p <= jj < j ==> (\forall integer kk; p <= kk < n ==> A[i][jj][kk] == B[i][jj][kk]);
		  loop assigns j, k, A[i][500 .. 999][500 .. 999];
		  loop variant n - j;
		*/
		while(j < n){
			k=p;
			/*@
			  loop invariant p <= k <= n;
			  loop invariant \forall integer kk; p <= kk < k ==> A[i][j][kk] == B[i][j][kk];
			  loop assigns k, A[i][j][500 .. 999];
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
	  loop assigns i, j, k;
	  loop variant n - i;
	*/
	while(i < n){
		j=0;
		k=0;
		/*@
		  loop invariant 0 <= j <= n;
		  loop assigns j, k;
		  loop variant n - j;
		*/
		while(j < n){
			k=0;
			/*@
			  loop invariant 0 <= k <= n;
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
