#include <assert.h>
#define SIZE 5
int array[SIZE];
int n=SIZE;
/*@
  requires n == SIZE;
  requires \valid(array + (0 .. n-1));
  assigns array[0 .. n-1];
*/
void SelectionSort()
{
   int lh, rh, i, temp;
   /*@
     loop invariant 0 <= lh <= n;
     loop assigns lh, rh, i, temp, array[0 .. n-1];
     loop variant n - lh;
   */
   for (lh = 0; lh < n; lh++) {
      rh = lh;
      /*@
        loop invariant lh+1 <= i <= n;
        loop invariant lh <= rh < n;
        loop invariant
        \forall integer j; lh <= j < i ==> array[rh] <= array[j];
        loop assigns i, rh;
        loop variant n - i;
      */
      for (i = lh + 1; i < n; i++) 
         if (array[i] < array[rh]) rh = i;
      temp = array[lh];
      array[lh] = array[rh];
      array[rh] = temp;
   }
}
int main(void){
	int array[SIZE],i;
	/*@
	  loop invariant -1 <= i <= SIZE-1;
	  loop invariant
	  \forall integer j; i < j < SIZE ==> array[j] == j;
	  loop assigns i, array[0 .. SIZE-1];
	  loop variant i + 1;
	*/
	for(i=SIZE-1; i>=0; i--)
		array[i]=i;
	SelectionSort();
	/*@
	  loop invariant 0 <= i <= SIZE;
	  loop invariant
	  \forall integer j; 0 <= j < i ==> array[j] == j;
	  loop assigns i;
	  loop variant SIZE - i;
	*/
	for(i=0; i<SIZE; i++){
		//@ assert(array[i]==i);
   }
}
