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
	int min;
	i=0;
	j=0;
	k=0;
	/*@
	  loop invariant 0 <= i <= m;
	  loop assigns i, j, k, A[0 .. 999][0 .. 1499][0 .. 1799];
	  loop variant m - i;
	*/
	while(i < m){
		j=0;
		k=0;
		/*@
		  loop invariant 0 <= j <= n;
		  loop assigns j, k, A[i][0 .. 1499][0 .. 1799];
		  loop variant n - j;
		*/
		while(j < n){
			k=0;
			/*@
			  loop invariant 0 <= k <= p;
			  loop assigns k, A[i][j][0 .. 1799];
			  loop variant p - k;
			*/
			while(k < p){
					A[i][j][k]= unknown();
					k=k+1;
			}
			j=j+1;
		}
		i=i+1;
    }
	i=0;
	j=0;
	k=0;
        min=A [0][0][0];
	/*@
	  loop invariant 0 <= i <= m;
	  loop invariant \forall integer a, b, c; 0 <= a < i && 0 <= b < n && 0 <= c < p ==> min <= A[a][b][c];
	  loop assigns i, j, k, min;
	  loop variant m - i;
	*/
	while(i < m){
		j=0;
		k=0;
		/*@
		  loop invariant 0 <= j <= n;
		  loop invariant \forall integer a, b, c; 0 <= a < i && 0 <= b < n && 0 <= c < p ==> min <= A[a][b][c];
		  loop invariant \forall integer b, c; 0 <= b < j && 0 <= c < p ==> min <= A[i][b][c];
		  loop assigns j, k, min;
		  loop variant n - j;
		*/
		while(j < n){
			k=0;
			/*@
			  loop invariant 0 <= k <= p;
			  loop invariant \forall integer a, b, c; 0 <= a < i && 0 <= b < n && 0 <= c < p ==> min <= A[a][b][c];
			  loop invariant \forall integer b, c; 0 <= b < j && 0 <= c < p ==> min <= A[i][b][c];
			  loop invariant \forall integer c; 0 <= c < k ==> min <= A[i][j][c];
			  loop assigns k, min;
			  loop variant p - k;
			*/
			while(k < p){
                                    if(A[i][j][k]<min){
					min=A[i][j][k];}
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
	  loop invariant \forall integer a, b, c; 0 <= a < m && 0 <= b < n && 0 <= c < p ==> min <= A[a][b][c];
	  loop assigns i, j, k;
	  loop variant m - i;
	*/
	while(i < m){
		j=0;
		k=0;
		/*@
		  loop invariant 0 <= j <= n;
		  loop invariant \forall integer a, b, c; 0 <= a < m && 0 <= b < n && 0 <= c < p ==> min <= A[a][b][c];
		  loop assigns j, k;
		  loop variant n - j;
		*/
		while(j < n){
			k=0;
			/*@
			  loop invariant 0 <= k <= p;
			  loop invariant \forall integer a, b, c; 0 <= a < m && 0 <= b < n && 0 <= c < p ==> min <= A[a][b][c];
			  loop assigns k;
			  loop variant p - k;
			*/
			while(k < p){
					//@ assert(A[i][j][k]>=min);
					k=k+1;
			}
			j=j+1;
		}
		i=i+1;
    }
return 0;
}
