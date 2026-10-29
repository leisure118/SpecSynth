#include<limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();
int main()
{
    int i;
    int n = 100000;
    int pos;
    int element = unknown();
    int found = 0;
    int vectorx[n];
		/*@
		  loop invariant 0 <= i <= n;
		  loop assigns i, vectorx[0 .. n-1];
		  loop variant n - i;
		*/
		for(i = 0; i < n; i++) 
		{
		  vectorx[i] = unknown();
		} 
    /*@
      loop invariant 0 <= i <= n;
      loop invariant 0 <= found <= 1;
      loop invariant found == 1 ==> (0 <= pos < i && vectorx[pos] == element && (\forall integer j; 0 <= j < pos ==> vectorx[j] != element));
      loop invariant found == 0 ==> (\forall integer j; 0 <= j < i ==> vectorx[j] != element);
      loop assigns i, found, pos;
      loop variant n - i;
    */
    for (i = 0; i < n && !found; i++)
    {
        if (vectorx[i] == element)
        {
            found = 1;
            pos = i;
        }
    }
    if ( found )
    {
        /*@
          loop invariant pos <= i <= n-1;
          loop assigns i, vectorx[pos .. n-2];
          loop variant (n-1) - i;
        */
        for (i = pos; i <  n - 1; i++)
        {
            vectorx[i] = vectorx[i + 1];
        }
    }
    if ( found ) {
      int x;
      /*@
        loop invariant 0 <= x <= pos;
        loop invariant \forall integer j; 0 <= j < pos ==> vectorx[j] != element;
        loop assigns x;
        loop variant pos - x;
      */
      for ( x = 0 ; x < pos ; x++ ) {
        //@ assert(vectorx[x] != element  );
      }
    }
  return 0;
}
