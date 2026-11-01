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
	int q=500,s=700;
	int A [1000][1500];
        int B [500][700];
	//@ assert(q<m);
	//@ assert(s<n);
	i=0;
	j=0;
	/*@
	  loop invariant 0 <= i <= m;
	  loop assigns i, j, B[0 .. 499][0 .. 699];
	  loop variant m - i;
	*/
	while(i < m){
		j=0;
		/*@
		  loop invariant 0 <= j <= n;
		  loop assigns j, B[i][0 .. 699];
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
	  loop invariant 0 <= i <= q;
	  loop invariant \forall integer a, b; 0 <= a < i && 0 <= b < s ==> A[a][b] == B[a][b];
	  loop assigns i, j, A[0 .. 499][0 .. 699];
	  loop variant q - i;
	*/
	while(i < q){
		j=0;
		/*@
		  loop invariant 0 <= j <= s;
		  loop invariant \forall integer b; 0 <= b < j ==> A[i][b] == B[i][b];
		  loop invariant \forall integer a, b; 0 <= a < i && 0 <= b < s ==> A[a][b] == B[a][b];
		  loop assigns j, A[i][0 .. 699];
		  loop variant s - j;
		*/
		while(j < s){
					A[i][j]=B[i][j];
			j=j+1;
		}
		i=i+1;
    }
	i=0;
	j=0;
	/*@
	  loop invariant 0 <= i <= q;
	  loop invariant \forall integer a, b; 0 <= a < q && 0 <= b < s ==> A[a][b] == B[a][b];
	  loop assigns i, j;
	  loop variant q - i;
	*/
	while(i < q){
		j=0;
		/*@
		  loop invariant 0 <= j <= s;
		  loop invariant \forall integer a, b; 0 <= a < q && 0 <= b < s ==> A[a][b] == B[a][b];
		  loop assigns j;
		  loop variant s - j;
		*/
		while(j < s){
                                //@ assert(A[i][j]==B[i][j]);
                                j=j+1;
		}
		i=i+1;
    }
return 0;
}
