#include<stdio.h>
/*@
	requires n>=0&&\valid_read(a+(0..n-1));
	assigns \nothing;
	ensures \forall integer k;0<=k<n==>\result>=a[k];
*/
int max(int a[], int n) {
	int max = a[0];
	int i = 0;
	/*@
		loop invariant 0<=i<=n;
		loop invariant \forall integer k;0<=k<i==>max>=a[k];
		loop assigns i,max;
		loop variant n-i;
	*/
	while(i<n) {
		if(a[i]>max) 
			max = a[i];
		i++;
	}
	return max;
}
int min(int a[], int n) {
	int min = a[0];
	int i = 0;
	while(i<n) {
		if(a[i]<min) 
			min = a[i];
		i++;
	}
	return min;
}
void main() {
	int a[] = {11, 23, 13, 16, 54, 59};
	int max_val = max(a, 6);
	//@ assert \forall integer k; 0 <= k < 6 ==> max_val >= a[k];
	int min_val = min(a, 6);
	//@ assert \forall integer k; 0 <= k < 6 ==> min_val <= a[k];
}