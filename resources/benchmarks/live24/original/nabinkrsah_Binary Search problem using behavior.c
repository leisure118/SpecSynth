#include<stdio.h>
/*@
predicate sorted(int* a, int length)=\forall integer i,j;0<=i<j<length==>a[i]<=a[j];
*/
int binary_search(int* a, int n, int v) {
	int l=0,u=n-1;
	while(l<=u) {
		int m=l+(u-l)/2;
		if(a[m]==v) return m;
		else if(a[m]<v) l=m+1;
		else u=m-1;
	}
	return -1;
}
void main() {
	int a[] = {1, 3, 4, 5, 9};
	int n = sizeof(a) / sizeof(a[0]);
	//@ assert sorted(a + 0, n);
	int res = binary_search(a, n, 5);
	//@ assert res==3;
}