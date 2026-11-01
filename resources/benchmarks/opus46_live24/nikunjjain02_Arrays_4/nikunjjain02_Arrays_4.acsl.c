#include<stdio.h>
/*@predicate sorted(int* a, integer length)=\forall integer i,j;0<=i<=j<length==>a[i]<=a[j];
*/
/*@
  requires n >= 1;
  requires \valid_read(a+(0..n-1));
  requires sorted(a, n);
  assigns \nothing;
  ensures \result == -1 || (0 <= \result < n && a[\result] == v);
  ensures \result == -1 ==> \forall integer i; 0 <= i < n ==> a[i] != v;
*/
int binary_search(int* a, int n, int v) {
	int l=0,u=n-1;
	/*@
	  loop invariant 0 <= l;
	  loop invariant u <= n - 1;
	  loop invariant \forall integer i; 0 <= i < l ==> a[i] < v;
	  loop invariant \forall integer i; u < i < n ==> a[i] > v;
	  loop assigns l, u;
	  loop variant u - l + 1;
	*/
	while(l<=u) {
		int m=l+(u-l)/2;
		if(a[m]==v) return m;
		else if(a[m]<v) l=m+1;
		else u=m-1;
	}
	return -1;
}
void main() {
	int _arr[] = {3,4,5,13,21};
	int *a = _arr;
	//@ assert sorted(a, 5);
	int res = binary_search(a, 5, 5);
	//@ assert res == 2;
}