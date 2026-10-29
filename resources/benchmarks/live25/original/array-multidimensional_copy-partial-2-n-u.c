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
	while(i < m){
		j=0;
		while(j < n){
					B[i][j]=unknown();
			j=j+1;
		}
		i=i+1;
    }
	i=0;
	j=0;
	while(i < q){
		j=0;
		while(j < s){
					A[i][j]=B[i][j];
			j=j+1;
		}
		i=i+1;
    }
	i=0;
	j=0;
	while(i < q){
		j=0;
		while(j < s){
                                //@ assert(A[i][j]==B[i][j]);
                                j=j+1;
		}
		i=i+1;
    }
return 0;
}
