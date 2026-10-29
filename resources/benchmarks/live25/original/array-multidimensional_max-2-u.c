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
	int A [1000][1500];
	int max;
	i=0;
	j=0;
	while(i < m){
		j=0;
		while(j < n){
					A[i][j]=unknown();
			j=j+1;
		}
		i=i+1;
    }
	i=0;
	j=0;
        max=A [0][0];
	while(i < n){
		j=0;
		while(j < n){
			if(A[i][j]>max){
                            max=A[i][j];
                        }
			j=j+1;
		}
		i=i+1;
    }
	i=0;
	j=0;
	while(i < n){
		j=0;
		while(j < n){
			//@ assert(A[i][j]<=max);
			j=j+1;
		}
		i=i+1;
    }
return 0;
}
