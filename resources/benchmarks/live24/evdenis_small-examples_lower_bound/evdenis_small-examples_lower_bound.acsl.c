/*@
  requires n > 0;
  requires \valid_read(a+(0 .. n-1));
  requires \forall integer i, j; 0 <= i <= j < n ==> a[i] <= a[j];
  assigns \nothing;
  ensures 0 <= \result <= n;
  ensures \forall integer i; 0 <= i < \result ==> a[i] < val;
  ensures \forall integer i; \result <= i < n ==> a[i] >= val;
*/
unsigned lower_bound(const int *a, unsigned n, int val)
{
	unsigned left = 0;
	unsigned right = n;
	unsigned middle = 0;
	/*@
	  loop invariant 0 <= left <= right <= n;
	  loop invariant \forall integer i; 0 <= i < left ==> a[i] < val;
	  loop invariant \forall integer i; right <= i < n ==> a[i] >= val;
	  loop invariant \forall integer i, j; 0 <= i <= j < n ==> a[i] <= a[j];
	  loop assigns left, right, middle;
	  loop variant right - left;
	*/
	while (left < right) {
		middle = left + (right - left) / 2;
		if (a[middle] < val) {
			//@ assert \forall integer i; 0 <= i < middle+1 ==> a[i] < val;
			left = middle + 1;
		} else right = middle;
	}
	return left;
}
int main(){
	unsigned n = 5;
	int a[5] = {1, 2, 3, 4, 5};
	unsigned result = lower_bound(a, n, 3);
	//@ assert result == 2;
	return 0;
}