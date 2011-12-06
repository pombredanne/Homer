Common Usecases for Homer:
These usecases express common concepts for Homer.


@key("title")
class Anime(Model):
    '''A model for Animes, who keep track of all its episode'''
    title = String()
    episodes = Set(Episode)
    
    def hits(self):
        '''Calculates the number of hits by adding hits from each episode'''
        numOfHits = 0
        for e in self.episodes:
            numOfHits += e.hits
        return numOfHits
    
    def rating(self):
        """Calulates the rating of this Anime by average rating of all its episodes"""
        rate = 0
        for e in self.episodes:
            rate += e.rating
        return rate/len(self.episodes)

@key("id")
class Product(Model):
    """A Product in the database..."""
    name = String("")
    likes = Integer(indexed = True)
    rating = Rating(indexed = True) #
    dateAdded = DateTime()
    quantity = Integer()
    video = Blob(size = "100MB", mime = "video/mp4")
    
    def id(self):
        '''Returns a unique identifier for this product'''
        return     

@Path("/recommend")
class Recommendations(Request):
    '''Recommendations and User FeedBack'''
    
    @GET("/{user}/{limit}")
    @Produces(Map(Integer, Product))
    def RecommendationsPerUser(self, user, limit):
        '''Returns {@link limit} number of recommendations for a particular User'''
        pass
    
    @POST("/{user}/liked/")
    @Consumes((Set(Product))
    def Liked(self, user, product):
        '''A post is done to this route when a User likes a Product'''
        pass
    
    @DELETE("/{user}/ignored/{product}")
    def Ignored(self, user, product):
        '''Invoked when a User ignores a particular Product'''
        pass
        
    
