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
	  loop invariant 0 <= i <= q;
	  loop invariant \forall integer p; 0 <= p < i ==> (\forall integer r; 0 <= r < s ==> A[p][r] == B[p][r]);
	  loop assigns i, j, A[0 .. q-1][0 .. s-1];
	  loop variant q - i;
	*/
	while(i < q){
		j=0;
		/*@
		  loop invariant 0 <= j <= s;
		  loop invariant \forall integer r; 0 <= r < j ==> A[i][r] == B[i][r];
		  loop assigns j, A[i][0 .. s-1];
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
	  loop invariant \forall integer p, r; 0 <= p < q && 0 <= r < s ==> A[p][r] == B[p][r];
	  loop assigns i, j;
	  loop variant q - i;
	*/
	while(i < q){
		j=0;
		/*@
		  loop invariant 0 <= j <= s;
		  loop invariant \forall integer p, r; 0 <= p < q && 0 <= r < s ==> A[p][r] == B[p][r];
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
