#include<stdio.h>
/*@predicate sorted(int* a, integer length)=\forall integer i,j;0<=i<=j<length==>a[i]<=a[j];
*/
/*@
  requires \valid(a+(0 .. n-1));
  requires n >= 0;
  requires \forall integer i,j; 0 <= i <= j < n ==> a[i] <= a[j];
  assigns \nothing;
  ensures \result == -1 || (0 <= \result < n && a[\result] == v);
  ensures \result >= 0 ==> a[\result] == v;
  ensures \result < 0 ==> \forall integer i; 0 <= i < n ==> a[i] != v;
*/
int binary_search(int* a, int n, int v) {
	int l=0,u=n-1;
	/*@
	  loop invariant 0 <= l <= u+1 <= n;
	  loop invariant \forall integer i; 0 <= i < n && a[i] == v ==> l <= i <= u;
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
	int data[] = {3,4,5,13,21};
	int* a = data;
	//@ assert a[0] == 3 && a[1] == 4 && a[2] == 5 && a[3] == 13 && a[4] == 21;
	//@ assert sorted(a, 5);
	//@ assert \forall integer i; 0 <= i < 5 && a[i] == 5 ==> i == 2;
	int res = binary_search(a, 5, 5);
	//@ assert a[0] == 3 && a[1] == 4 && a[2] == 5 && a[3] == 13 && a[4] == 21;
	//@ assert a[res] == 5;
	//@ assert res == 2;
}