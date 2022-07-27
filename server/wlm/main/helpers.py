

def take_snapshot():
    """
    New monuments + Update to monuments data
    New Approved/Unapproved monuments
    New pictures
    Aggregate data on geographic entities #TODO: evaluate on-the-fly aggregation with aggressive caching (break on import and pre-caching)
    """    
    pass


def update_geo():
    """
    Updates the geographic entities
    No historical tracking of changes
    # TODO: UNDERSTAND HOW TO HANDLE PREVIOUS AGGREGATIONS 
    # PROBABLY: we should drop and recompute stats for each snapshot. or use on the-fly aggregation + (pre-)caching.
    Potientially this could "move" a Monument from one municipality (or indirectly province or region) to another.
    """
    pass