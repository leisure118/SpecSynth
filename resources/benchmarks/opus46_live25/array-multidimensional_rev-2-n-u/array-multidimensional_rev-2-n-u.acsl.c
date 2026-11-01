#include<limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();
int main()
{
	int i,j;
	int m=1000,n=1500,p=1800;
	int A [1000][1500];
	int B [1000][1500];
	i=0;
	j=0;
	/*@
	  loop invariant 0 <= i <= m;
	  loop assigns i, j, B[0 .. m-1][0 .. n-1];
	  loop variant m - i;
	*/
	while(i < m){
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
	  loop invariant 0 <= i <= m;
	  loop invariant \forall integer ii, jj; 0 <= ii < i && 0 <= jj < n ==> A[ii][jj] == B[m-ii-1][n-jj-1];
	  loop assigns i, j, A[0 .. m-1][0 .. n-1];
	  loop variant m - i;
	*/
	while(i < m){
		j=0;
		/*@
		  loop invariant 0 <= j <= n;
		  loop invariant \forall integer jj; 0 <= jj < j ==> A[i][jj] == B[m-i-1][n-jj-1];
		  loop assigns j, A[i][0 .. n-1];
		  loop variant n - j;
		*/
		while(j < n){
                            A[i][j]=B[m-i-1][n-j-1];
			j=j+1;
		}
		i=i+1;
    }
	i=0;
	j=0;
	/*@
	  loop invariant 0 <= i <= m;
	  loop invariant \forall integer ii, jj; 0 <= ii < m && 0 <= jj < n ==> A[ii][jj] == B[m-ii-1][n-jj-1];
	  loop assigns i, j;
	  loop variant m - i;
	*/
	while(i < m){
		j=0;
		/*@
		  loop invariant 0 <= j <= n;
		  loop invariant \forall integer ii, jj; 0 <= ii < m && 0 <= jj < n ==> A[ii][jj] == B[m-ii-1][n-jj-1];
		  loop assigns j;
		  loop variant n - j;
		*/
		while(j < n){
                            //@ assert(A[i][j]==B[m-i-1][n-j-1]);
			j=j+1;
		}
		i=i+1;
    }
return 0;
}
