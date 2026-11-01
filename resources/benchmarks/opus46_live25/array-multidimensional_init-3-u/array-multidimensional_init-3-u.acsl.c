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
	int C=unknown();
	i=0;
	j=0;
	k=0;
	/*@
	  loop invariant 0 <= i <= n;
	  loop invariant \forall integer x, y, z; 0 <= x < i && 0 <= y < n && 0 <= z < n ==> A[x][y][z] == C;
	  loop assigns i, j, k, A[0 .. n-1][0 .. n-1][0 .. n-1];
	  loop variant n - i;
	*/
	while(i < n){
		j=0;
		k=0;
		/*@
		  loop invariant 0 <= j <= n;
		  loop invariant \forall integer y, z; 0 <= y < j && 0 <= z < n ==> A[i][y][z] == C;
		  loop assigns j, k, A[i][0 .. n-1][0 .. n-1];
		  loop variant n - j;
		*/
		while(j < n){
			k=0;
			/*@
			  loop invariant 0 <= k <= n;
			  loop invariant \forall integer z; 0 <= z < k ==> A[i][j][z] == C;
			  loop assigns k, A[i][j][0 .. n-1];
			  loop variant n - k;
			*/
			while(k < n){
					A[i][j][k]=C;
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
	  loop invariant \forall integer x, y, z; 0 <= x < n && 0 <= y < n && 0 <= z < n ==> A[x][y][z] == C;
	  loop assigns i, j, k;
	  loop variant n - i;
	*/
	while(i < n){
		j=0;
		k=0;
		/*@
		  loop invariant 0 <= j <= n;
		  loop invariant \forall integer x, y, z; 0 <= x < n && 0 <= y < n && 0 <= z < n ==> A[x][y][z] == C;
		  loop assigns j, k;
		  loop variant n - j;
		*/
		while(j < n){
			k=0;
			/*@
			  loop invariant 0 <= k <= n;
			  loop invariant \forall integer x, y, z; 0 <= x < n && 0 <= y < n && 0 <= z < n ==> A[x][y][z] == C;
			  loop assigns k;
			  loop variant n - k;
			*/
			while(k < n){
					//@ assert(A[i][j][k]==C);
					k=k+1;
			}
			j=j+1;
		}
		i=i+1;
    }
return 0;
}
