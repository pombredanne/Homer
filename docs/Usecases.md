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
  
@key("name")
class Episode(Model):
    """An Episode of an Anime"""
    name = String()
    hits = Integer(indexed = True)
    rating = Rating(indexed = True)
    video = Blob(size = "100MB", mime = "video/mp4")
    
