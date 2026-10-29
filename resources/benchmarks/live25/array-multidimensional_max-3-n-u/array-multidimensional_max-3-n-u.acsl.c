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
	int max;
	//@ ghost int old_max_record;
	//@ ghost int g_mid_max;
	i=0;
	j=0;
	k=0;
	/*@
	  loop invariant 0 <= i <= m;
	  loop assigns i, j, k, A[0 .. m-1][0 .. n-1][0 .. p-1];
	  loop variant m - i;
	*/
	while(i < m){
		j=0;
		k=0;
		/*@
		  loop invariant 0 <= j <= n;
		  loop assigns j, k, A[i][0 .. n-1][0 .. p-1];
		  loop variant n - j;
		*/
		while(j < n){
			k=0;
			/*@
			  loop invariant 0 <= k <= p;
			  loop assigns k, A[i][j][0 .. p-1];
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
        max=A [0][0][0];
	/*@
	  loop invariant 0 <= i <= m;
	  loop invariant \forall integer ii, jj, kk; 0 <= ii < i && 0 <= jj < n && 0 <= kk < p ==> A[ii][jj][kk] <= max;
	  loop assigns i, j, k, max, old_max_record, g_mid_max;
	  loop variant m - i;
	*/
	while(i < m){
		j=0;
		k=0;
		//@ ghost g_mid_max = max;
		/*@
		  loop invariant 0 <= j <= n;
		  loop invariant \forall integer jj, kk; 0 <= jj < j && 0 <= kk < p ==> A[i][jj][kk] <= max;
		  loop invariant max >= g_mid_max;
		  loop assigns j, k, max, old_max_record;
		  loop variant n - j;
		*/
		while(j < n){
			k=0;
			//@ ghost old_max_record = max;
			/*@
			  loop invariant 0 <= k <= p;
			  loop invariant \forall integer kk; 0 <= kk < k ==> A[i][j][kk] <= max;
			  loop invariant max >= old_max_record;
			  loop assigns k, max;
			  loop variant p - k;
			*/
			while(k < p){
                                    if(A[i][j][k]>max){
						max=A[i][j][k];}
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
	  loop invariant \forall integer ii, jj, kk; 0 <= ii < i && 0 <= jj < n && 0 <= kk < p ==> A[ii][jj][kk] <= max;
	  loop invariant \forall integer ii, jj, kk; 0 <= ii < m && 0 <= jj < n && 0 <= kk < p ==> A[ii][jj][kk] <= max;
	  loop assigns i, j, k;
	  loop variant m - i;
	*/
	while(i < m){
		j=0;
		k=0;
		/*@
		  loop invariant 0 <= j <= n;
		  loop invariant \forall integer jj, kk; 0 <= jj < j && 0 <= kk < p ==> A[i][jj][kk] <= max;
		  loop invariant \forall integer ii, jj, kk; 0 <= ii < m && 0 <= jj < n && 0 <= kk < p ==> A[ii][jj][kk] <= max;
		  loop assigns j, k;
		  loop variant n - j;
		*/
		while(j < n){
			k=0;
			/*@
			  loop invariant 0 <= k <= p;
			  loop invariant \forall integer kk; 0 <= kk < k ==> A[i][j][kk] <= max;
			  loop invariant \forall integer ii, jj, kk; 0 <= ii < m && 0 <= jj < n && 0 <= kk < p ==> A[ii][jj][kk] <= max;
			  loop assigns k;
			  loop variant p - k;
			*/
			while(k < p){
					//@ assert(A[i][j][k]<=max);
					k=k+1;
			}
			j=j+1;
		}
		i=i+1;
    }
	return 0;
}
