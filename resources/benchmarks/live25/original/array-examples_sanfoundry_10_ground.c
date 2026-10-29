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
		for(i = 0; i < n; i++) 
		{
		  vectorx[i] = unknown();
		} 
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
        for (i = pos; i <  n - 1; i++)
        {
            vectorx[i] = vectorx[i + 1];
        }
    }
    if ( found ) {
      int x;
      for ( x = 0 ; x < pos ; x++ ) {
        //@ assert(vectorx[x] != element  );
      }
    }
  return 0;
}
