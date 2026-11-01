/*@
  requires size > 0;
  requires \valid(arr + (0 .. size-1));
  requires addr < size;
  requires 0 <= arr[addr];
  requires arr[addr] < (int)size;
  assigns arr[0 .. size-1];
  ensures arr[\old(arr[addr])] == 0;
  ensures \forall integer i; 0 <= i < size && i != \old(arr[addr]) ==> arr[i] == \old(arr[i]);
*/
void indaddr(unsigned size, int arr[size], unsigned addr)
{
	arr[arr[addr]] = 0;
}
int main(){
	unsigned size = 5;
	int arr[5] = {1, 2, 3, 4, 5};
	indaddr(size, arr, 2);
	//@ assert arr[3] == 0;
}
